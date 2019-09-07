import re

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from accounts.forms import RestaurantForm
from accounts.models import *
from browse.forms import PackageForm
from browse.models import Ingredient, IngredientList, PackageBranchDetails, Package
from manager.utils_db import *


class IndexView(TemplateView):
	template_name = 'manager/index.html'

	def get(self, request, *args, **kwargs):
		if self.request.user.is_authenticated:
			return redirect(reverse('homepage'))
		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = {'loggedIn': self.request.user.is_authenticated}
		return context


class ProcessOrdersView(TemplateView):
	template_name = 'manager/manage_order.html'

	def get_context_data(self, **kwargs):
		branch = RestaurantBranch.objects.get(user=self.request.user)
		obj_list = Order.objects.filter(branch=branch)  # .order_by('status', '-time')
		print(branch)
		print('-----')
		return {'object_list': obj_list, 'branch': branch}


class EditRestaurantView(TemplateView):
	template_name = 'manager/edit_restaurant.html'

	def get(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect(reverse('index'))
		if request.user.is_branch_manager:
			return redirect('/orders/')
		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(EditRestaurantView, self).get_context_data(kwargs=kwargs)
		if self.request.user.is_authenticated and self.request.user.is_manager:
			context['restaurant'] = User.objects.get(id=self.request.user.id).restaurant
		return context

	def post(self, request, *args, **kwargs):
		print(request)
		profile = User.objects.get(id=self.request.user.id).restaurant
		profile.user = request.user
		profile_form = RestaurantForm(
			request.POST or None, request.FILES or None, instance=profile)
		print(profile_form)
		if profile_form.is_valid():
			profile_form.save()
			print('Registering : ' + str(request.user))
			return render(request, 'manager/message_page.html',
						  {'header': "Done !", 'details': 'Successfully edited the profile'})

		else:
			return render(request, 'manager/message_page.html',
						  {'header': "Sorry !", 'details': 'Try again'})


class AddMenuView(TemplateView):
	template_name = 'manager/add_menu.html'

	def get(self, request, *args, **kwargs):
		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(AddMenuView, self).get_context_data()
		context['ingredient_list'] = Ingredient.objects.all()
		return context

	def post(self, request, *args, **kwargs):
		restaurant = User.objects.get(id=self.request.user.id).restaurant
		print(request.POST)
		menu_form = PackageForm(request.POST or None, request.FILES or None)
		ingrd_list = request.POST.getlist('ingrds')[0].split(',')
		print(menu_form)
		if menu_form.is_valid():
			menu = menu_form.save(commit=False)
			menu.restaurant = restaurant
			print(menu)
			menu.save()
			for tmp in ingrd_list:
				tmp = " ".join(re.sub('[^a-zA-Z]+', ',', tmp.lower()).split(','))
				ingrd, created = Ingredient.objects.get_or_create(name=tmp.strip())
				IngredientList.objects.create(package=menu, ingredient=ingrd)
			PackageBranchDetails.add_package_to_all_branches(restaurant=restaurant, package=menu)
			return render(request, 'manager/message_page.html',
						  {'header': "Done !", 'details': 'Menu added succcessfully'})

		else:
			return render(request, 'manager/message_page.html',
						  {'header': "Sorry !", 'details': 'Couldnot add up menu'})


class EditMenuView(TemplateView):
	template_name = 'manager/edit_menu.html'

	def get(self, request, *args, **kwargs):
		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		""" Prevent Accessing Other Restaurants Package """
		id = kwargs['id']
		pkg = Package.objects.get(id=id)
		if not pkg.is_editable(self.request.user):
			pkg = None
			ing_list = None
		else:
			ing_list = [ingobj.ingredient.name for ingobj in IngredientList.objects.filter(package=pkg)]
		# comments = PackageReview.objects.filter(package=pkg)
		user_id = self.request.user.id if self.request.user.is_authenticated else 0
		ctx = {'loggedIn': self.request.user.is_authenticated, 'item': pkg, 'item_img': [pkg.image],
		       'ing_list': ing_list
		       }
		return ctx

	def post(self, request, *args, **kwargs):
		id = kwargs['id']

		pkg = Package.objects.get(id=id)
		if not pkg.is_editable(self.request.user):
			return HttpResponse("<h1>Access Error: Not permitted to edit for current user<h1>")
		restaurant = User.objects.get(id=self.request.user.id).restaurant
		print(request.POST)
		menu_form = PackageForm(request.POST or None, request.FILES or None, instance=pkg)
		ingrd_list = request.POST.getlist('ingrds')[0].split(',')
		print(menu_form)
		if menu_form.is_valid():
			menu = menu_form.save(commit=False)
			menu.restaurant = restaurant
			print(menu)
			menu.save()
			for tmp in ingrd_list:
				tmp = " ".join(re.sub('[^a-zA-Z]+', ',', tmp.lower()).split(','))
				ingrd, created = Ingredient.objects.get_or_create(name=tmp.strip())
				IngredientList.objects.get_or_create(package=menu, ingredient=ingrd)
			PackageBranchDetails.add_package_to_all_branches(restaurant=restaurant, package=menu)
			return render(request, 'manager/message_page.html',
						  {'header': "Done !", 'details': 'Menu added succcessfully'})

		else:
			return render(request, 'manager/message_page.html',
			              {'header': "Sorry !", 'details': 'Couldnot add up menu'})


def DeliveryAvailability(request):
	print(request)
	id = request.POST.get('id')
	status = request.POST.get('delivery_option')
	print(id)
	branch = RestaurantBranch.objects.get(id=id)
	if status == 'close_delivery':
		branch.running = False
	else:
		branch.running = True

	branch.save()


def acceptOrder(request):
	order_id = request.POST.get('order_id')
	order = Order.objects.get(id=order_id)
	order.order_status = order.PROCESSING
	order.save()
	from customer.utils_db import send_notification
	send_notification(order.user.id, "Your order:" + str(
		order.id) + " from " + order.branch.branch_name + " has been confirmed and pending for delivery.")
	return JsonResponse({'order': 'placed'})


class ViewMenusView(TemplateView):
	template_name = 'manager/manage_menus.html'

	def get_context_data(self, **kwargs):
		restaurant = User.objects.get(id=self.request.user.id).restaurant
		obj_list = Package.objects.filter(restaurant=restaurant)  # .order_by('status', '-time')
		print(obj_list)
		print('-----')
		return {'menu_list': obj_list}


class ViewBranchMenusView(TemplateView):
	template_name = 'manager/manage_branchMenus.html'

	def get_context_data(self, **kwargs):
		return {'menu_list': get_packages_list_branch(self.request.user)}


def branch_pkg_details(request):
	return render(request, 'manager/branch_pkg_modal.html',
	              {'pkg': get_package_branch(request.user, request.GET.get('id'))})


def offerSubmit(request):
	id = request.POST.get('id')
	discount = request.POST.get('discount_amnt')
	buy_amnt = request.POST.get('buy_amnt')
	get_amnt = request.POST.get('get_amnt')
	offer_type = request.POST.get('offer_type')
	start_date = request.POST.get('start_date')
	end_date = request.POST.get('end_date')
	print(start_date, ' ', end_date)
	if offer_type == 'buy_get':
		offer_type = 'B'
	elif offer_type == 'discount':
		offer_type = 'D'
	elif offer_type == 'none':
		offer_type = 'N'
	if offer_type == PackageBranchDetails.DISCOUNT:
		update_offer_branch(request.user, id, offer_type, start_date, end_date, discount_val=discount)
	elif offer_type == PackageBranchDetails.BUY_N_GET_N:
		update_offer_branch(request.user, id, offer_type, start_date, end_date, buy_n=buy_amnt, get_n=get_amnt)
	elif offer_type == PackageBranchDetails.NONE:
		update_offer_branch(request.user, id, offer_type, start_date, end_date)
	return JsonResponse({'updated': True})


def submitPkg_Availabilty(request):
	id = request.POST.get('pkg_id')

	is_available = True if request.POST.get('is_available') == 'True' else False
	print(id)
	is_available = True if request.POST.get('is_available') == 'True' else False
	return JsonResponse({'availability': set_package_availability_branch(request.user, id, is_available)})


class ManagerDashBoardView(TemplateView):
	template_name = 'manager/manager_dashboard.html'

	def get(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect(reverse('index'))

		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(ManagerDashBoardView, self).get_context_data(kwargs=kwargs)
		if self.request.user.is_authenticated and self.request.user.is_manager:
			import datetime
			today = datetime.date.today()
			context['order_cnt'] = Order.objects.filter(branch__restaurant=self.request.user.restaurant,
			                                            time__month=today.month, time__year=today.year).count()
			context['monthly_revenue'] = sum(pkg.price for ord in
			                                 Order.objects.filter(branch__restaurant=self.request.user.restaurant,
			                                                      time__month=today.month) for pkg in
			                                 ord.get_package_list())
			context['item_cnt'] = Package.objects.filter(restaurant=self.request.user.restaurant,
			                                             available=True).count()
			context['branch_cnt'] = RestaurantBranch.objects.filter(restaurant=self.request.user.restaurant).count()
			context['months'] = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
			                     "October", "November", "December"]
			context['branches'] = get_monthwise_order_completed_count_restaurant(
				rest_id=self.request.user.restaurant.id)
			context['menus'] = get_packagewise_order_completed_count_restaurant(rest_id=self.request.user.restaurant.id,
			                                                                    last_n_months=3)
		return context


class BranchManagerDashBoardView(TemplateView):
	template_name = 'manager/branch_dashboard.html'

	def get(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect(reverse('index'))

		return super(self.__class__, self).get(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(BranchManagerDashBoardView, self).get_context_data(kwargs=kwargs)
		if self.request.user.is_authenticated and self.request.user.is_branch_manager:
			context['order_cnt'] = 3
			context['monthly_revenue'] = 30
			context['item_cnt'] = 30
			context['unique_customer'] = 4
			context['months'] = ["January", "February", "March", "April", "May", "June", "July"]
			context['branch'] = {'sale': [28, 48, 40, 19, 86, 27, 90], 'fillColor': "rgba(220,0,220,0.3)"}
			context['menus'] = [{'name': 'burger', 'sale': 200, 'fillColor': "rgba(220,0,220,0.3)"} ,
								   {'name': 'pizza', 'sale' : 500 ,'fillColor': "rgba(0,220,220,0.3)"}
								   ]
		return context



def delivery_info(request):
	from delivery.views import delivery_details
	return delivery_details(request)